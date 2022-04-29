<template>
  <v-container v-if="localState.image">
      <v-row v-for="tag in localState.image.tags" :key="tag">
        <v-col>
          <hsk-text-input :label="'Pull '+tag" :static-value="'library://'+localState.image.pullUrl(tag)">
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
          <hsk-text-input label="Created" :static-value="localState.image.createdAt | moment('YYYY-MM-DD HH:mm:ss')"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input label="Created By" :static-value="localState.image.createdBy"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input 
            label="Description" 
            field="description" 
            :obj="localState.image" 
            action="images/update"
            :readonly="!canEdit"
            @updated="localState.image=$event"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input label="Hash" :static-value="localState.image.hash"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input label="Size" :static-value="localState.image.size | prettyBytes()"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input type="yesno" label="Signed" :static-value="localState.image.signed"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input type="yesno" label="Verified" :static-value="localState.image.signatureVerified"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input type="yesno" label="Encrypted" :static-value="localState.image.encrypted"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <hsk-text-input label="Uploaded" :static-value="localState.image.uploadState"></hsk-text-input>
        </v-col>
        <v-col>
          <hsk-text-input label="Downloads" :static-value="localState.image.downloadCount"></hsk-text-input>
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
  image?: Image;
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
      image: undefined,
    }
  }),
  mounted: function() {
    this.localState.image = this.image;
  },
  computed: {
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    canEdit(): boolean {
      return !this.readonly && (this.localState.image?.canEdit ?? false)
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