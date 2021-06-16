<template>
  <v-container v-if="image">
      <v-row v-for="tag in image.tags" :key="tag">
        <v-col>
          <hsk-text-input :label="'Pull '+tag" :static-value="'library://'+image.pullUrl(tag)">
            <template v-slot:append v-if="canEdit">
              <v-icon color="error" @click="deleteTag(tag)">mdi-delete-outline</v-icon>
            </template>
          </hsk-text-input>
        </v-col>
      </v-row>
      <v-row v-if="canEdit">
        <v-col class="text-center">
            <v-dialog v-model="localState.showAddTag" max-width="300px">
              <template v-slot:activator="{ on, attrs }">
                <v-btn color="primary" text v-bind="attrs" v-on="on">
                  <v-icon>mdi-tag-plus</v-icon> Add Tag
                </v-btn>
              </template>
              <v-card>
                <v-card-title class="headline">Add Tag</v-card-title>
                <v-card-text>
                  <v-form v-model="localState.newTagValid">
                    <v-text-field 
                      v-model="localState.newTag" 
                      label="New Tag" 
                      solo 
                      :rules="[checkTag]"
                      required></v-text-field>
                  </v-form>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="warning accent-1" text @click="closeShowAddTag()">Nej, tack</v-btn>
                  <v-btn color="success darken-1" text @click="addTag()" :disabled="!localState.newTagValid">Do it!</v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>

        </v-col>
      </v-row>

      <v-row>
        <v-col>
          <hsk-text-input label="Created" :static-value="image.createdAt | moment('YYYY-MM-DD HH:mm:ss')"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input label="Created By" :static-value="image.createdBy"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input 
            label="Description" 
            field="description" 
            :obj="image" 
            action="images/update"
            :readonly="!canEdit"
            @updated="image=$event"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input label="Hash" :static-value="image.hash"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input label="Size" :static-value="image.size | prettyBytes()"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input type="yesno" label="Signed" :static-value="image.signed"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input type="yesno" label="Verified" :static-value="image.signatureVerified"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input type="yesno" label="Encrypted" :static-value="image.encrypted"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input type="yesno" label="Uploaded" :static-value="image.uploaded"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input label="Downloads" :static-value="image.downloadCount"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row v-if="canEdit">
        <v-col class="text-center">
          <v-dialog v-model="localState.showDelete" max-width="500px">
            <template v-slot:activator="{ on, attrs }">
              <v-btn text v-bind="attrs" v-on="on" color="error">
                <v-icon>mdi-trash</v-icon> Delete Image
              </v-btn>
            </template>
            <v-card>
              <v-card-title class="headline">You sure you won't miss it?</v-card-title>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary darken-1" text @click="localState.showDelete=false">Let's keep it for now.</v-btn>
                <v-btn color="warning accent-1" text @click="deleteImage()">Get it out of my sight!</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-col>
      </v-row>

  </v-container>
</template>
<script lang="ts">
import { Image, User, checkName } from '@/store/models';
import Vue from 'vue';

import { clone as _clone, filter as _filter, concat as _concat } from 'lodash';

interface State {
  newTag: string;
  newTagValid: boolean;
  showAddTag: boolean;
  showDelete: boolean;
}

export default Vue.extend({
  name: 'SingularityDetails',
  props: {
    image: {
      type: Image,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  data: (): { localState: State } => ({
    localState: {
      newTag: '',
      showAddTag: false,
      showDelete: false,
      newTagValid: true,
    }
  }),
  computed: {
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    canEdit(): boolean {
      return !this.readonly && this.image.canEdit(this.currentUser)
    },
  },
  watch: {
    'localState.showAddTag': function showAddTag(val) {
      if (!val) {
        this.closeShowAddTag();
      }
    },
  },
  methods: {
    deleteTag(tag: string) {
      const updateImage = _clone(this.image);
      updateImage.tags = _filter(updateImage.tags, t => t !== tag);
      this.saveTags(updateImage)
        .then(() => this.$store.commit('snackbar/showSuccess', 'Tag removed.'))
    },
    addTag() {
      const updateImage = _clone(this.image);
      updateImage.tags = _concat(updateImage.tags, this.localState.newTag);
      this.saveTags(updateImage)
        .then(() => {
          this.$store.commit('snackbar/showSuccess', 'Tag added');
          this.closeShowAddTag();
        });
    },
    saveTags(updateImage: Image): Promise<any> {
      return this.$store.dispatch('images/updateTags', updateImage)
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    deleteImage() {
      this.$store.dispatch('images/delete', this.image)
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    },
    closeShowAddTag() {
      this.localState.showAddTag = false;
      this.$nextTick(() => {
        this.localState.newTag = '';
      });
    },
    checkTag(name: string): string | boolean {
      if (name === '' || name === undefined) {
        return "Required";
      }
      else {
        return checkName(name);
      }
    },
  }
});
</script>