<template>
   <v-expansion-panel v-if="image">
    <v-expansion-panel-header>
      <v-row no-gutters>
        <v-col>
          <span v-if="image.tags.length==0">
            <v-chip color="yellow lighten-2">
              <v-icon left>mdi-alert-circle-outline</v-icon>
              No tags
            </v-chip>
          </span>
          <span>
            <v-chip 
              color="green lighten-1" 
              v-for="tag in image.tags" :key="tag" 
              @click.stop="copyTag(tag)">
                {{tag}}
            </v-chip>
          </span>
        </v-col>
        <v-col class="d-flex align-center">
          <v-btn text icon @click.stop="inspect()">
            <v-icon large>mdi-file-code-outline</v-icon>
            <v-dialog v-model="localState.showDef">
              <v-card>
                <v-card-title class="headline green lighten-2">
                  Singularity Definition
                </v-card-title>
                <v-card-text>
                  <pre class="text--primary">{{localState.meta.deffile}}</pre>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="primary" text @click="localState.showDef = false">
                    What a nice definition file!
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </v-btn>
          <v-badge :content="image.downloadCount || '0'" overlap color="blue-grey lighten-1">
            <v-icon large>mdi-download</v-icon>
          </v-badge>
          <v-tooltip bottom v-if="image.signed">
            <template v-slot:activator="{ on, attrs }">
              <v-icon v-bind="attrs" v-on="on" large class="ml-2">mdi-seal</v-icon>
            </template>
            <span>Signed</span>
          </v-tooltip>
          <v-tooltip bottom v-if="image.signatureVerified">
            <template v-slot:activator="{ on, attrs }">
              <v-icon v-bind="attrs" v-on="on" large>mdi-check-decagram</v-icon>
            </template>
            <span>Valid Signature</span>
          </v-tooltip>
        </v-col>
      </v-row>
    </v-expansion-panel-header> 
    <v-expansion-panel-content>
      <singularity-details :image="image" :readonly="readonly"></singularity-details>
    </v-expansion-panel-content>
   </v-expansion-panel>
</template>
<script lang="ts">
import { Image, InspectAttributes, } from '@/store/models';
import SingularityDetails from '@/components/SingularityDetails.vue';
import Vue from 'vue';

interface State {
  meta: InspectAttributes;
  showDef: boolean;
}

export default Vue.extend({
  components: { SingularityDetails },
  name: 'ImageDetails',
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
      meta: {
        deffile: '',
      },
      showDef: false,
    },
  }),
  computed: {
  },
  methods: {
    copyTag(tag: string) {
      this.$copyText(`library://${this.image.pullUrl(tag)}`)
        .then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard."));
    },
    inspect() {
      this.$store.dispatch('images/inspect', this.image)
        .then(response => {
          console.log(response);
          this.localState.meta = response;
          this.localState.showDef = true;
        })
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    },
  }
});
</script>